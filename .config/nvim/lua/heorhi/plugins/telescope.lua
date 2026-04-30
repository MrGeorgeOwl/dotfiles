return {
	"nvim-telescope/telescope.nvim",
	dependencies = { "nvim-lua/plenary.nvim" },
	config = function()
		local ignored_names = {
			".venv",
			".git",
			".idea",
			"__pycache__",
			".ruff_cache",
			".pytest_cache",
			".mypy_cache",
		}

		local function escape_lua_pattern(value)
			return value:gsub("([%^%$%(%)%%%.%[%]%*%+%-%?])", "%%%1")
		end

		local file_ignore_patterns = {}
		local live_grep_args = {
			"--hidden",
			"--no-ignore",
		}

		for _, name in ipairs(ignored_names) do
			table.insert(file_ignore_patterns, escape_lua_pattern(name) .. "$")
			table.insert(file_ignore_patterns, escape_lua_pattern(name) .. "/")
			table.insert(live_grep_args, "--glob")
			table.insert(live_grep_args, "!**/" .. name)
			table.insert(live_grep_args, "--glob")
			table.insert(live_grep_args, "!**/" .. name .. "/**")
		end

		require("telescope").setup({
			defaults = {
				file_ignore_patterns = file_ignore_patterns,
			},
		})

		local builtin = require("telescope.builtin")
		vim.keymap.set("n", "<leader>ff", function()
			builtin.find_files({
				hidden = true,
				no_ignore = true,
				no_ignore_parent = true,
			})
		end, {})
		vim.keymap.set("n", "<leader>fg", function()
			builtin.live_grep({
				additional_args = function()
					return live_grep_args
				end,
			})
		end, {})
	end,
}
