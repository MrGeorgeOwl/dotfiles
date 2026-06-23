vim.g.mapleader = " "
vim.keymap.set("n", "<leader>pf", vim.cmd.Ex)

function insertFullPath()
	local filepath = vim.fn.expand("%")
	vim.fn.setreg("+", filepath) -- write to clipboard
end
vim.keymap.set("n", "<leader>pc", insertFullPath, { noremap = true, silent = true })

vim.keymap.set("n", "<leader>pr", function()
	vim.cmd("vertical Diff review ++layout=split")
end, { noremap = true, silent = true })
