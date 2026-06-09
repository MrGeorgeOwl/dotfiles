return {
    'tpope/vim-fugitive',
    config = function()
        local function get_git_status()
            vim.cmd("Gedit :")
        end

        local function open_to_right()
            local status_buf = vim.api.nvim_get_current_buf()
            local cfile = vim.fn["fugitive#PorcelainCfile"]()

            if cfile == "" then
                return
            end

            local target_win = vim.b.fugitive_right_win

            if target_win ~= nil and vim.api.nvim_win_is_valid(target_win) then
                vim.api.nvim_set_current_win(target_win)
                vim.cmd("edit " .. cfile)
                return
            end

            vim.cmd("rightbelow Gvsplit " .. cfile)
            vim.api.nvim_buf_set_var(status_buf, "fugitive_right_win", vim.api.nvim_get_current_win())
        end

        local function edit_keymaps()
            if vim.b.fugitive_type ~= "index" then
                return
            end

            vim.keymap.set("n", "<CR>", open_to_right, { buffer = true })
            vim.keymap.set("n", "o", open_to_right, { buffer = true })
        end

        vim.keymap.set("n", "<leader>gs", get_git_status)

        vim.api.nvim_create_autocmd("User", {
            pattern = "FugitiveIndex",
            callback = edit_keymaps,
        })
    end
}
