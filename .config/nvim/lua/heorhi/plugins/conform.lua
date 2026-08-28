return {
    'stevearc/conform.nvim',
    opts = {},
    config = function()
        require("conform").setup({
            formatters_by_ft = {
                lua = { "stylua" },
                python = { "ruff_fix", "ruff_organize_imports", "ruff_format" },
                rust = { "rustfmt" },
                javascript = { "prettierd", "prettier", stop_after_first = true },
            },
            format_on_save = function(bufnr)
                local bufname = vim.api.nvim_buf_get_name(bufnr)
                -- ignoring work directory
                if bufname:match("/splitmetrics/") then
                    return
                end
                return {
                    timeout_ms = 500,
                    lsp_format = "fallback",
                }
            end
        })
    end
}
