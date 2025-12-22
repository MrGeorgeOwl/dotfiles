# GPU
sudo pacman -S mesa \
	lib32-mesa \
	vulkan-radeon \
	lib32-vulkan-radeon \
	libva-mesa-driver \
	lib32-libva-mesa-driver \
	mesa-utils \
	pciutils \
	vulkan-tools

# Audio
sudo pacman -S pipewire \
	pipewire-alsa \
	pipewire-pulse \
	pipewire-jack \
	wireplumber \
	pavucontrol \
	alsa-utils

# Desktop & utilities
sudo pacman -S hyprland \
	xdg-desktop-portal-hyprland \
	qt5-wayland \
	qt6-wayland \
	alacritty \
	waybar \
	wofi \
	mako \
	grim \
	slurp \
	wl-clipboard \
	polkit-kde-agent \
	ttf-nerd-fonts-symbols ttf-nerd-fonts-symbols-mono ttf-jetbrains-mono-nerd
