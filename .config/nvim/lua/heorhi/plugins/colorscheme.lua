return {
    {
        "folke/tokyonight.nvim",
        name = "colorscheme",
        priority = 1000,
        config = function()
            vim.cmd([[colorscheme tokyonight]])
        end,
    },
}
