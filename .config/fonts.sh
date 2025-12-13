# https://github.com/davgar99/arch-linux-font-improvement-guide
sudo pacman -S noto-fonts \
    noto-fonts-cjk \
    noto-fonts-emoji \
    noto-fonts-extra \
    ttf-liberation \
    ttf-dejavu \
    ttf-roboto \
    ttf-jetbrains-mono \
    ttf-fira-code \
    ttf-hack \
    adobe-source-code-pro-fonts

sudo ln -s /usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf /etc/fonts/conf.d/
