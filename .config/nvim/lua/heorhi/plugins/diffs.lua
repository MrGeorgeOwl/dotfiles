return {
	"barrettruth/diffs.nvim",
	lazy = false,
	init = function()
		local diff_colors = {
			add_bg = "#e6f4ea",
			add_text_bg = "#d8eadc",
			add_fg = "#2f7d48",
			delete_bg = "#f9e7e3",
			delete_text_bg = "#efcfc8",
			delete_fg = "#b14538",
			base_bg = "#f4ecd8",
			base_fg = "#9a6b20",
		}

		vim.g.diffs = {
			highlights = {
				overrides = {
					DiffsAdd = { bg = diff_colors.add_bg },
					DiffsAddText = { bg = diff_colors.add_text_bg },
					DiffsAddBar = { fg = diff_colors.add_fg, bg = diff_colors.add_bg },
					DiffsAddRailNr = { fg = diff_colors.add_fg, bg = diff_colors.add_bg, nocombine = true },

					DiffsDelete = { bg = diff_colors.delete_bg },
					DiffsDeleteText = { bg = diff_colors.delete_text_bg },
					DiffsDeleteBar = { fg = diff_colors.delete_fg, bg = diff_colors.delete_bg },
					DiffsDeleteRailNr = { fg = diff_colors.delete_fg, bg = diff_colors.delete_bg, nocombine = true },

					DiffsConflictOurs = { bg = diff_colors.delete_bg },
					DiffsConflictOursNr = { fg = diff_colors.delete_fg, bg = diff_colors.delete_bg },
					DiffsConflictTheirs = { bg = diff_colors.add_bg },
					DiffsConflictTheirsNr = { fg = diff_colors.add_fg, bg = diff_colors.add_bg },
					DiffsConflictBase = { bg = diff_colors.base_bg },
					DiffsConflictBaseNr = { fg = diff_colors.base_fg, bg = diff_colors.base_bg },
				},
			},
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
