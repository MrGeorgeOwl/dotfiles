vim.g.mapleader = " "

local function project_structure_root()
	local buffer_name = vim.api.nvim_buf_get_name(0)
	local start = vim.fn.getcwd()

	if buffer_name ~= "" and not buffer_name:match("^%w+://") then
		if vim.fn.isdirectory(buffer_name) == 1 then
			start = buffer_name
		elseif vim.fn.filereadable(buffer_name) == 1 then
			start = vim.fs.dirname(buffer_name)
		end
	end

	return vim.fs.root(start, { ".git" }) or start
end

local function open_project_structure()
	vim.cmd("Explore " .. vim.fn.fnameescape(project_structure_root()))
end

vim.keymap.set("n", "<leader>pf", open_project_structure, { desc = "Open project structure" })

function insertFullPath()
	local filepath = vim.fn.expand("%")
	vim.fn.setreg("+", filepath) -- write to clipboard
end
vim.keymap.set("n", "<leader>pc", insertFullPath, { noremap = true, silent = true })

