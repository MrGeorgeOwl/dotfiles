return {
    "tyru/open-browser.vim",
    config = function()
        local function open_url()
            local origin_win = vim.api.nvim_get_current_win()

            -- creating the input buffer
            local input_buf = vim.api.nvim_create_buf(false, true)
            vim.bo[input_buf].buftype = "nofile"
            vim.bo[input_buf].bufhidden = "wipe"
            vim.bo[input_buf].swapfile = false

            -- creating the window
            local max_width = math.max(1, vim.o.columns - 2)
            local width = math.min(72, max_width)
            local height = 1
            local window_height = height + 2
            local window_width = width + 2
            local input_win = vim.api.nvim_open_win(input_buf, true, {
                relative = "editor",
                row = math.max(0, math.floor((vim.o.lines - window_height) / 2)),
                col = math.max(0, math.floor((vim.o.columns - window_width) / 2)),
                width = width,
                height = height,
                style = "minimal",
                border = "single",
                title = " Open URL ",
                title_pos = "left",
                zindex = 50,
            })
            vim.wo[input_win].winhighlight = "Normal:NormalFloat,FloatBorder:FloatBorder,FloatTitle:Title"

            -- state
            local closed = false
            local submitted = false

            local function close_prompt()
                if closed then
                    return
                end

                if vim.api.nvim_get_current_win() == input_win then
                    vim.cmd.stopinsert()
                end

                closed = true
                if vim.api.nvim_win_is_valid(input_win) then
                    pcall(vim.api.nvim_win_close, input_win, true)
                end
                if vim.api.nvim_win_is_valid(origin_win) then
                    vim.api.nvim_set_current_win(origin_win)
                end
            end

            local function submit_url()
                if submitted or closed or not vim.api.nvim_buf_is_valid(input_buf) then
                    return
                end

                submitted = true
                local url = vim.api.nvim_buf_get_lines(input_buf, 0, 1, false)[1] or ""
                close_prompt()
                if url == "" then
                    return
                end

                vim.api.nvim_cmd({ cmd = "OpenBrowser", args = { url } }, {})
            end

            vim.keymap.set({ "i", "n" }, "<CR>", submit_url, { buffer = input_buf })
            vim.keymap.set({ "i", "n" }, "<Esc>", close_prompt, { buffer = input_buf })
            vim.keymap.set({ "i", "n" }, "<C-c>", close_prompt, { buffer = input_buf })
            vim.cmd.startinsert()
        end

        local function open_repository_url()
            vim.cmd("GBrowse :")
        end

        vim.keymap.set("n", "<leader>obt", open_url, { desc = "Open URL in browser" })
        vim.keymap.set("n", "<leader>obg", open_repository_url, { desc = "Open Git repository in browser" })
    end,
}
