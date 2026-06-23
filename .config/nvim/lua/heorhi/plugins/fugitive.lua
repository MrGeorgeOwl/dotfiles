return {
    'tpope/vim-fugitive',
    config = function()
        local function get_git_status()
            vim.cmd("only")
            vim.cmd("Gedit :")
        end

        vim.keymap.set("n", "<leader>gs", get_git_status)
    end
}
