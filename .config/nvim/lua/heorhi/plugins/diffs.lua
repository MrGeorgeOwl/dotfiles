local pierre_diffs_colors = {
	light = {
		add = "#0dbe4e",
		delete = "#ff2e3f",
		modified = "#009fff",
	},
	dark = {
		add = "#5ecc71",
		delete = "#ff6762",
		modified = "#69b1ff",
	},
}

local function normal_bg()
	local ok, normal = pcall(vim.api.nvim_get_hl, 0, { name = "Normal" })
	if ok then
		return normal.bg
	end
end

local function int_to_hex(color)
	return string.format("#%06x", color)
end

local function hex_to_rgb(color)
	local value = tonumber(color:sub(2), 16)

	return math.floor(value / 0x10000) % 0x100, math.floor(value / 0x100) % 0x100, value % 0x100
end

local function blend(fg, bg, alpha)
	local fr, fg_, fb = hex_to_rgb(fg)
	local br, bg_, bb = hex_to_rgb(bg)
	local function channel(fg_channel, bg_channel)
		return math.floor(fg_channel * alpha + bg_channel * (1 - alpha) + 0.5)
	end

	return string.format("#%02x%02x%02x", channel(fr, br), channel(fg_, bg_), channel(fb, bb))
end

local function is_dark_theme()
	local bg = normal_bg()
	if bg then
		local r = math.floor(bg / 0x10000) % 0x100
		local g = math.floor(bg / 0x100) % 0x100
		local b = bg % 0x100
		local luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

		return luminance < 128
	end

	return vim.o.background == "dark"
end

local function diff_colors()
	local dark = is_dark_theme()
	local colors = dark and pierre_diffs_colors.dark or pierre_diffs_colors.light
	local bg = normal_bg()
	local bg_hex = bg and int_to_hex(bg) or (dark and "#000000" or "#ffffff")
	local line_alpha = dark and 0.2 or 0.12
	local text_alpha = dark and 0.32 or 0.22
	local base_alpha = dark and 0.18 or 0.1

	return {
		add_bg = blend(colors.add, bg_hex, line_alpha),
		add_text_bg = blend(colors.add, bg_hex, text_alpha),
		add_fg = colors.add,
		delete_bg = blend(colors.delete, bg_hex, line_alpha),
		delete_text_bg = blend(colors.delete, bg_hex, text_alpha),
		delete_fg = colors.delete,
		base_bg = blend(colors.modified, bg_hex, base_alpha),
		base_fg = colors.modified,
	}
end

local function diff_highlight_overrides()
	local colors = diff_colors()

	return {
		DiffsAdd = { bg = colors.add_bg },
		DiffsAddText = { bg = colors.add_text_bg },
		DiffsAddBar = { fg = colors.add_fg, bg = colors.add_bg },
		DiffsAddRailNr = { fg = colors.add_fg, bg = colors.add_bg, nocombine = true },

		DiffsDelete = { bg = colors.delete_bg },
		DiffsDeleteText = { bg = colors.delete_text_bg },
		DiffsDeleteBar = { fg = colors.delete_fg, bg = colors.delete_bg },
		DiffsDeleteRailNr = { fg = colors.delete_fg, bg = colors.delete_bg, nocombine = true },

		DiffsConflictOurs = { bg = colors.delete_bg },
		DiffsConflictOursNr = { fg = colors.delete_fg, bg = colors.delete_bg },
		DiffsConflictTheirs = { bg = colors.add_bg },
		DiffsConflictTheirsNr = { fg = colors.add_fg, bg = colors.add_bg },
		DiffsConflictBase = { bg = colors.base_bg },
		DiffsConflictBaseNr = { fg = colors.base_fg, bg = colors.base_bg },
	}
end

local function apply_diff_highlights()
	for group, highlight in pairs(diff_highlight_overrides()) do
		vim.api.nvim_set_hl(0, group, highlight)
	end
end

local function configure_diffs()
	vim.g.diffs = vim.tbl_deep_extend("force", vim.g.diffs or {}, {
		highlights = {
			overrides = diff_highlight_overrides(),
		},
		integrations = {
			fugitive = true,
			gitsigns = true,
		},
	})
end

return {
	"barrettruth/diffs.nvim",
	lazy = false,
	init = function()
		configure_diffs()

		local group = vim.api.nvim_create_augroup("heorhi_diffs_highlights", { clear = true })
		local function refresh_highlights()
			configure_diffs()
			vim.schedule(apply_diff_highlights)
		end

		vim.api.nvim_create_autocmd("ColorScheme", {
			group = group,
			callback = refresh_highlights,
		})
		vim.api.nvim_create_autocmd("OptionSet", {
			group = group,
			pattern = "background",
			callback = refresh_highlights,
		})
		vim.api.nvim_create_autocmd("FileType", {
			group = group,
			pattern = { "git", "gitcommit", "fugitive" },
			callback = refresh_highlights,
		})
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
			"<leader>prh",
			function()
				vim.cmd("Diff review ++layout=split HEAD")
			end,
			desc = "Review uncommitted changes vs HEAD",
		},
		{
			"<leader>prf",
			function()
				local source_win = vim.api.nvim_get_current_win()

				-- diffs.nvim opens a single-file diff in a split; adopt that buffer into
				-- the current window so the diff replaces the file in place. <C-o> still
				-- returns to the source, since nvim_win_set_buf records the jump.
				if not pcall(vim.cmd, "Diff") then
					return
				end

				local diff_win = vim.api.nvim_get_current_win()
				if diff_win == source_win then
					return -- nothing opened (e.g. no changes)
				end

				local diff_buf = vim.api.nvim_get_current_buf()
				vim.api.nvim_set_current_win(source_win)
				vim.api.nvim_win_set_buf(source_win, diff_buf)
				vim.api.nvim_win_close(diff_win, true)
			end,
			desc = "Diff current file",
		},
	},
}
