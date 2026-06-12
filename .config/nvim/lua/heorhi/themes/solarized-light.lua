return {
	"maxmx03/solarized.nvim",
	lazy = false,
	priority = 1000,
	---@type solarized.config
	opts = {},
	config = function(_, opts)
		vim.o.termguicolors = true
		vim.o.background = "light"
		require("solarized").setup(opts)
		vim.cmd.colorscheme("solarized")

		local normal = vim.api.nvim_get_hl(0, { name = "Normal" })

		for _, group in ipairs({
			"LineNr",
			"LineNrAbove",
			"LineNrBelow",
			"CursorLineNr",
			"SignColumn",
			"FoldColumn",
		}) do
			local highlight = vim.api.nvim_get_hl(0, { name = group })
			highlight.bg = normal.bg
			vim.api.nvim_set_hl(0, group, highlight)
		end
	end,
}
