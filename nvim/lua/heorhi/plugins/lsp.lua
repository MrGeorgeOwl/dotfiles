return {
    'VonHeikemen/lsp-zero.nvim', branch = 'v3.x',
	dependencies = {
	    'neovim/nvim-lspconfig',
		'hrsh7th/cmp-nvim-lsp',
		'hrsh7th/nvim-cmp',
		'L3MON4D3/LuaSnip',
		"williamboman/mason.nvim",
		"williamboman/mason-lspconfig.nvim",
	},
	config = function()
		local cmp = require('cmp')
        local lsp_zero = require('lsp-zero')

		local cmp_select = { behavior = cmp.SelectBehavior.Select }

        cmp.setup({
            snippet = {
                expand = function(args)
                    require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
                end,
            },
            mapping = cmp.mapping.preset.insert({
                ['<C-p>'] = cmp.mapping.select_prev_item(cmp_select),
                ['<C-n>'] = cmp.mapping.select_next_item(cmp_select),
                ['<C-y>'] = cmp.mapping.confirm({ select = true }),
                ["<C-Space>"] = cmp.mapping.complete(),
            }),
            sources = cmp.config.sources({
                { name = 'nvim_lsp' },
                { name = 'luasnip' }, -- For luasnip users.
            }, {
                { name = 'buffer' },
            })
        })

        lsp_zero.on_attach(function(client, bufnr)
            lsp_zero.default_keymaps({buffer = bufnr})
            -- Mappings.
            local opts = { noremap=true, silent=true }
            -- See `:help vim.lsp.*` for documentation on any of the below functions
            vim.keymap.set('n', 'gD', function() vim.lsp.buf.declaration() end, opts)
            vim.keymap.set('n', 'gd', function() vim.lsp.buf.definition() end, opts)
            vim.keymap.set('n', '<C-K>', function() vim.lsp.buf.hover() end, opts)
            vim.keymap.set('n', 'gi', function() vim.lsp.buf.implementation() end, opts)
            vim.keymap.set('n', '<C-k>', function() vim.lsp.buf.signature_help() end, opts)
            vim.keymap.set('n', '<space>rn', function() vim.lsp.buf.rename() end, opts)
            vim.keymap.set('n', '<space>ca', function() vim.lsp.buf.code_action() end, opts)
            vim.keymap.set('n', 'gr', function() vim.lsp.buf.references() end, opts)
            vim.keymap.set('n', '<space>e', function() vim.diagnostic.open_float() end, opts)
        end)

        lsp_zero.setup()
		local cmp_lsp = require('cmp_nvim_lsp')
		local capabilities = vim.tbl_deep_extend(
			"force",
			{},
			vim.lsp.protocol.make_client_capabilities(),
			cmp_lsp.default_capabilities()
		)

		require('mason').setup()
		require('mason-lspconfig').setup({
			ensure_installed = {
				"lua_ls",
				"rust_analyzer",
				"pyright",
			},
			handlers = {
				function(server_name)
					require("lspconfig")[server_name].setup {
						capabilities = capabilities,
					}
				end,
				["lua_ls"] = function()
					local lspconfig = require('lspconfig')
					lspconfig.lua_ls.setup {
						capabilities = capabilities,
						settings = {
							Lua = {
								runtime = { version = "Lua 5.1" },
								diagnostics = {
									globals = { "bit", "vim", "it", "describe", "before_each", "after_each" },
								}
							}
						}
					}
				end,
			}
		})
	end
}
