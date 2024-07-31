-- Autoformat
vim.api.nvim_create_augroup("AutoFormat", {})

vim.api.nvim_create_autocmd(
    "BufWritePost",
    {
        pattern = "*.py",
        group = "AutoFormat",
        callback = function()
            vim.cmd("silent !ruff format --quiet %")
            vim.cmd("edit")
        end,
    }
)
vim.api.nvim_create_autocmd(
    "BufWritePost",
    {
        pattern = "*.rs",
        group = "AutoFormat",
        callback = function()
            vim.cmd("silent !cargo fmt --quiet -- %")
            vim.cmd("edit")
        end,
    }
)
