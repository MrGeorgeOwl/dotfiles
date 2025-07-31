return {
    "stevearc/aerial.nvim",
    config = function ()
        require('aerial').setup()
        vim.keymap.set("n", "<leader>a", "<cmd>AerialToggle!<CR>")
        vim.keymap.set("n", "<leader>na", "<cmd>AerialNext<CR>")
        vim.keymap.set("n", "<leader>pa", "<cmd>AerialPrev<CR>")
        vim.keymap.set("n", "<leader>nba", "<cmd>AerialNavToggle<CR>")
    end
}
