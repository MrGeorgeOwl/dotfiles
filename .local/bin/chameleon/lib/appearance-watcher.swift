import AppKit
import Darwin

func log(_ message: String) {
    FileHandle.standardError.write(Data("chameleon watch: \(message)\n".utf8))
}

guard CommandLine.arguments.count == 5 else {
    log("expected command, light theme, dark theme and lock path")
    exit(2)
}

// Only one listener may apply themes at a time, including foreground instances.
let lockFD = open(CommandLine.arguments[4], O_CREAT | O_RDWR, S_IRUSR | S_IWUSR)
guard lockFD >= 0, flock(lockFD, LOCK_EX | LOCK_NB) == 0 else {
    log("another watcher is already running (or the lock is inaccessible)")
    exit(1)
}
// Do not let the theme subprocess inherit ownership of the lock.
_ = fcntl(lockFD, F_SETFD, FD_CLOEXEC)

@MainActor
final class AppearanceWatcher: NSObject {
    let command: String
    let lightTheme: String
    let darkTheme: String
    var desired = ""
    var lastAttempted = ""
    var child: Process?
    var pendingRead: DispatchWorkItem?
    var stopping = false
    var signalSources: [DispatchSourceSignal] = []
    var appearanceObservation: NSKeyValueObservation?

    init(command: String, light: String, dark: String) {
        self.command = command
        lightTheme = light
        darkTheme = dark
        super.init()
    }

    func appearance() -> String {
        let match = NSApplication.shared.effectiveAppearance.bestMatch(from: [.aqua, .darkAqua])
        return match == .darkAqua ? "dark" : "light"
    }

    func applyLatest() {
        guard !stopping, child == nil, desired != lastAttempted else { return }
        lastAttempted = desired
        let theme = desired == "dark" ? darkTheme : lightTheme
        let process = Process()
        process.executableURL = URL(fileURLWithPath: command)
        process.arguments = ["-v", "--", theme]
        var environment = ProcessInfo.processInfo.environment
        environment["CHAMELEON_FOLLOW_APPEARANCE"] = "1"
        process.environment = environment
        process.terminationHandler = { finished in
            DispatchQueue.main.async {
                self.child = nil
                if finished.terminationStatus != 0 {
                    log("applying \(theme) failed (status \(finished.terminationStatus)); retry on next transition or restart")
                }
                // Changes during execution coalesce into the latest state.
                self.applyLatest()
            }
        }
        child = process
        do {
            log("\(desired) → \(theme)")
            try process.run()
        } catch {
            child = nil
            log("cannot run Chameleon: \(error)")
        }
    }

    func refresh() {
        desired = appearance()
        applyLatest()
    }

    func scheduleRefresh() {
        pendingRead?.cancel()
        let work = DispatchWorkItem { self.refresh() }
        pendingRead = work
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25, execute: work)
    }

    @objc nonisolated func interfaceThemeChanged(_ notification: Notification) {
        DispatchQueue.main.async { self.scheduleRefresh() }
    }

    func start() {
        // AppKit observes the real system appearance, including Settings changes
        // that do not publish the legacy distributed notification.
        appearanceObservation = NSApplication.shared.observe(\.effectiveAppearance,
                                                             options: [.new]) { _, _ in
            DispatchQueue.main.async { self.scheduleRefresh() }
        }
        // Widely used but undocumented by Apple. Read the actual preference:
        // duplicate notifications do not necessarily mean a transition.
        // The block-based API defaults to coalescing while the receiving process
        // is suspended. A background LaunchAgent must explicitly request delivery,
        // even when the sender (e.g. System Settings) does not force it.
        DistributedNotificationCenter.default().addObserver(
            self, selector: #selector(interfaceThemeChanged(_:)),
            name: Notification.Name("AppleInterfaceThemeChangedNotification"),
            object: nil, suspensionBehavior: .deliverImmediately
        )
        for number in [SIGTERM, SIGINT] {
            signal(number, SIG_IGN)
            let source = DispatchSource.makeSignalSource(signal: number, queue: .main)
            source.setEventHandler {
                self.stopping = true
                self.pendingRead?.cancel()
                if let process = self.child, process.isRunning {
                    process.terminate()
                    process.waitUntilExit()
                }
                exit(0)
            }
            source.resume()
            signalSources.append(source)
        }
        refresh()
    }
}

let application = NSApplication.shared
application.setActivationPolicy(.prohibited)
DispatchQueue.main.async {
    let watcher = AppearanceWatcher(command: CommandLine.arguments[1],
                                    light: CommandLine.arguments[2],
                                    dark: CommandLine.arguments[3])
    watcher.start()
}
application.run()
