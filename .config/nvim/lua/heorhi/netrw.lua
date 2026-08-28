local api = vim.api
local fn = vim.fn

local group = api.nvim_create_augroup("heorhi_netrw_filename_hover", { clear = true })
local refresh_events = { "CursorMoved", "CursorMovedI", "WinEnter", "BufWinEnter" }
local clear_events = { "BufLeave", "BufWinLeave", "WinLeave" }

local function clear_filename_highlight(win)
	local previous_match = vim.w[win].netrw_filename_hover_match

	if previous_match then
		pcall(fn.matchdelete, previous_match, win)
		vim.w[win].netrw_filename_hover_match = nil
	end
end

local function filename_range(line)
	local first = line:find("%S")
	local last = line:match(".*()%S")

	if not first or not last then
		return nil
	end

	return { fn.line("."), first, last - first + 1 }
end

local function highlight_filename()
	local win = api.nvim_get_current_win()

	clear_filename_highlight(win)

	local range = filename_range(api.nvim_get_current_line())
	if not range then
		return
	end

	vim.w[win].netrw_filename_hover_match = fn.matchaddpos("CursorLine", { range }, 10, -1, { window = win })
end

local function clear_current_window_highlight()
	clear_filename_highlight(api.nvim_get_current_win())
end

api.nvim_create_autocmd("FileType", {
	group = group,
	pattern = "netrw",
	callback = function(event)
		if vim.b[event.buf].netrw_filename_hover_configured then
			return
		end

		vim.b[event.buf].netrw_filename_hover_configured = true
		vim.opt_local.cursorline = false

		api.nvim_create_autocmd(refresh_events, {
			group = group,
			buffer = event.buf,
			callback = highlight_filename,
		})

		api.nvim_create_autocmd(clear_events, {
			group = group,
			buffer = event.buf,
			callback = clear_current_window_highlight,
		})

		highlight_filename()
	end,
})
