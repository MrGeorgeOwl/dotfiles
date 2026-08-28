for _, path in ipairs(vim.fn.glob(vim.fn.stdpath("data") .. "/lazy/*", false, true)) do
	vim.opt.rtp:append(path)
end

package.loaded["heorhi.plugins.colorscheme"] = nil

local spec = require("heorhi.plugins.colorscheme")

if type(spec.config) == "function" then
	spec.config(spec, spec.opts or {})
end

vim.cmd("redraw!")
