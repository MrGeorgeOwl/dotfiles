return {
	"barrettruth/diffs.nvim",
	lazy = false,
	init = function()
		vim.g.diffs = {
			integrations = {
				fugitive = true,
				gitsigns = true,
			},
		}
	end,
}
