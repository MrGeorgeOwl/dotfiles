return {
	"tpope/vim-fugitive",
	dependencies = {
		"tpope/vim-rhubarb",
		"tyru/open-browser.vim",
	},
	config = function()
		local function get_git_status()
			vim.cmd("Gedit :")
			if #vim.api.nvim_list_wins() > 1 then
				vim.cmd("only")
			end
		end

		vim.keymap.set("n", "<leader>gs", get_git_status)
	end,
}
