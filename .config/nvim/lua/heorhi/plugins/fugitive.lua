return {
    'tpope/vim-fugitive',
    config = function()
        local function get_git_status()
            vim.cmd("Gedit :")
        end

        local function open_to_right()
            local cfile = vim.fn["fugitive#Cfile"]()

            if cfile == "" then
                return
            end

            vim.cmd("rightbelow Gvsplit " .. cfile)
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
