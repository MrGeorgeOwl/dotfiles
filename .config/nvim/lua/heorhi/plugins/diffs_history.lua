local function notify(message, level)
	vim.notify(message, level or vim.log.levels.WARN, { title = "diffs.nvim history" })
end

local function git(args)
	local output = vim.fn.systemlist(vim.list_extend({ "git" }, args))
	return output, vim.v.shell_error
end

local function close_popup(win, buf)
	if win and vim.api.nvim_win_is_valid(win) then
		vim.api.nvim_win_close(win, true)
	end
	if buf and vim.api.nvim_buf_is_valid(buf) then
		vim.api.nvim_buf_delete(buf, { force = true })
	end
end

local function open_commit_diff(hash, root)
	if vim.fn.exists(":Diff") ~= 2 then
		notify("diffs.nvim :Diff command is unavailable", vim.log.levels.ERROR)
		return
	end

	local parents, status = git({ "-C", root, "rev-list", "--parents", "-n", "1", hash })
	if status ~= 0 or not parents[1] or parents[1] == "" then
		notify("Could not resolve commit parents for " .. hash, vim.log.levels.ERROR)
		return
	end

	-- Review shows a commit against its first parent. The root commit has none, and
	-- diffs.nvim requires a commit on the base side, so there is nothing to diff against.
	local parent = parents[1]:match("^%S+%s+(%S+)")
	if not parent then
		notify("Commit " .. hash .. " is the root commit; nothing to diff against")
		return
	end

	local spec = parent .. ".." .. hash
	local ok, err = pcall(vim.cmd, "Diff review ++layout=split " .. spec)
	if not ok then
		notify("Could not open diffs.nvim review for " .. hash .. ": " .. tostring(err), vim.log.levels.ERROR)
	end
end

local function open_history()
	local repo_root, root_status = git({ "rev-parse", "--show-toplevel" })
	if root_status ~= 0 or not repo_root[1] or repo_root[1] == "" then
		notify("Current directory is not inside a git repository")
		return
	end
	local root = repo_root[1]

	local commits, log_status = git({ "-C", root, "log", "--format=%h %s" })
	if log_status ~= 0 then
		notify("git log failed", vim.log.levels.ERROR)
		return
	end
	if #commits == 0 then
		notify("Git history is empty")
		return
	end

	local title = " Git commits "
	local content_width = vim.fn.strdisplaywidth(title)
	for _, commit in ipairs(commits) do
		content_width = math.max(content_width, vim.fn.strdisplaywidth(commit))
	end

	-- Padding comes from an empty fold gutter on the left (set on the window
	-- below) plus matching slack on the right, so the window must be wide enough
	-- for the gutter, the text, and the right margin. Keep a screen-edge margin.
	local pad = 2
	local width = math.max(40, math.min(content_width + pad * 2, vim.o.columns - 8))
	local height = math.min(#commits, math.max(1, math.floor(vim.o.lines * 0.6)))
	local row = math.max(0, math.floor((vim.o.lines - height) / 2 - 1))
	local col = math.max(0, math.floor((vim.o.columns - width) / 2))

	local buf = vim.api.nvim_create_buf(false, true)
	vim.bo[buf].buftype = "nofile"
	vim.bo[buf].bufhidden = "wipe"
	vim.bo[buf].swapfile = false

	-- Naming the buffer fires BufFilePost, which makes plugins like gitsigns try to
	-- attach to this throwaway scratch buffer. Suppress autocommands while we do it.
	local saved_eventignore = vim.o.eventignore
	vim.o.eventignore = "all"
	local named_ok = pcall(vim.api.nvim_buf_set_name, buf, "diffs://commit-history")
	vim.o.eventignore = saved_eventignore
	if not named_ok then
		notify("Could not name commit-history buffer", vim.log.levels.DEBUG)
	end

	vim.api.nvim_buf_set_lines(buf, 0, -1, false, commits)
	vim.bo[buf].modifiable = false

	local win = vim.api.nvim_open_win(buf, true, {
		relative = "editor",
		style = "minimal",
		border = "rounded",
		title = title,
		title_pos = "center",
		row = row,
		col = col,
		width = width,
		height = height,
	})
	-- Left padding via an empty fold gutter keeps the buffer text unpadded; blend
	-- the gutter highlights into the float so it just reads as padding.
	vim.wo[win].foldcolumn = tostring(pad)
	vim.wo[win].winhighlight = "FoldColumn:NormalFloat,CursorLineFold:CursorLine"
	vim.wo[win].cursorline = true

	local function close()
		close_popup(win, buf)
	end

	local function select_commit()
		local hash = vim.api.nvim_get_current_line():match("^(%S+)")
		if not hash then
			notify("Could not read commit hash from selection")
			return
		end

		close()
		open_commit_diff(hash, root)
	end

	local map_opts = { buffer = buf, nowait = true, silent = true }
	vim.keymap.set("n", "<CR>", select_commit, map_opts)
	vim.keymap.set("n", "q", close, map_opts)
	vim.keymap.set("n", "<Esc>", close, map_opts)
end

return {
	"barrettruth/diffs.nvim",
	keys = {
		{
			"<leader>prt",
			open_history,
			desc = "Show git commit history diff",
		},
	},
}
