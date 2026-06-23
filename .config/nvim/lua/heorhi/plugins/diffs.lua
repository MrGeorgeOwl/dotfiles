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
	keys = {
		{
			"<leader>pr",
			function()
				vim.cmd("vertical Diff review ++layout=split")
			end,
			desc = "Diff review",
		},
		{
			"<leader>prf",
			function()
				vim.cmd("vertical Diff")
			end,
			desc = "Diff current file",
		},
	},
}
