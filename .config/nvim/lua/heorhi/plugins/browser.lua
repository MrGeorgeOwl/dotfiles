return {
	"tyru/open-browser.vim",
	config = function()
		local function open_url()
			vim.ui.input({ prompt = "Open URL: " }, function(url)
				if not url or url == "" then
					return
				end

				vim.api.nvim_cmd({ cmd = "OpenBrowser", args = { url } }, {})
			end)
		end

		local function open_repository_url()
			vim.cmd("GBrowse :")
		end

		vim.keymap.set("n", "<leader>obt", open_url, { desc = "Open URL in browser" })
		vim.keymap.set("n", "<leader>obg", open_repository_url, { desc = "Open Git repository in browser" })
	end,
}
