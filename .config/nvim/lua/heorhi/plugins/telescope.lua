return {
    'nvim-telescope/telescope.nvim',
    dependencies = { 'nvim-lua/plenary.nvim' },
    config = function()
        require('telescope').setup({
            defaults = {
                file_ignore_patterns = {
                    '%.venv/',
                    '%.git/',
                },
            },
        })

        local builtin = require('telescope.builtin')
        vim.keymap.set('n', '<leader>ff', function()
            builtin.find_files({
                hidden = true,
                no_ignore = true,
                no_ignore_parent = true,
            })
        end, {})
        vim.keymap.set('n', '<leader>fg', function()
            builtin.live_grep({
                additional_args = function()
                    return {
                        '--hidden',
                        '--no-ignore',
                        '--glob',
                        '!**/.venv/**',
                        '--glob',
                        '!**/.git/**',
                    }
                end,
            })
        end, {})
    end
}
