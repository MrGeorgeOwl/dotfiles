vim.g.mapleader = " "

local function project_structure_directory()
	local buffer_name = vim.api.nvim_buf_get_name(0)

	if buffer_name ~= "" and not buffer_name:match("^%w+://") then
		if vim.fn.isdirectory(buffer_name) == 1 then
			return buffer_name
		end

		local directory = vim.fs.dirname(buffer_name)
		if directory and vim.fn.isdirectory(directory) == 1 then
			return directory
		end
	end

	local cwd = vim.fn.getcwd()
	return vim.fs.root(cwd, { ".git" }) or cwd
end

local function open_project_structure()
	vim.cmd("Explore " .. vim.fn.fnameescape(project_structure_directory()))
end

vim.keymap.set("n", "<leader>pf", open_project_structure, { desc = "Open project structure" })

function insertFullPath()
	local filepath = vim.fn.expand("%")
	vim.fn.setreg("+", filepath) -- write to clipboard
end
vim.keymap.set("n", "<leader>pc", insertFullPath, { noremap = true, silent = true })

