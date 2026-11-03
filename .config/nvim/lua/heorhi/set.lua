vim.opt.nu = true
vim.opt.relativenumber = true
vim.opt.clipboard = "unnamedplus"

-- Inside herdr, panes may lack WAYLAND_DISPLAY, so wl-copy is unreliable.
-- Copy via OSC 52: herdr forwards it to the attached client's clipboard
-- (Ghostty locally, the MacBook when attached remotely).
-- Paste uses Neovim's own register; paste external text with the terminal's paste key.
if vim.env.HERDR_ENV then
	local osc52 = require("vim.ui.clipboard.osc52")
	local function paste()
		return { vim.fn.split(vim.fn.getreg(""), "\n"), vim.fn.getregtype("") }
	end
	vim.g.clipboard = {
		name = "OSC 52 (herdr)",
		copy = { ["+"] = osc52.copy("+"), ["*"] = osc52.copy("*") },
		paste = { ["+"] = paste, ["*"] = paste },
	}
end

vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

vim.opt.smartindent = true

vim.opt.hlsearch = false
vim.opt.incsearch = true

vim.opt.scrolloff = 15
vim.opt.splitright = true

vim.opt.updatetime = 50

vim.opt.termguicolors = true
