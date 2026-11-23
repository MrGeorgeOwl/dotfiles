import { View, div } from "gpui-kit";
import { checking, closeOverlay, layout, props, run } from "herdr";

const VIEW = "changes";

function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

export default class TogglePanelView extends View {
  init() {
    if (checking()) return;
    closeOverlay(props().overlay);
    const root = layout(), panel = find(root, "panel"), body = find(root, "panel-body");
    if (!panel.hidden && body.active === VIEW) return run("layout.hide", { id: "panel" });
    run("layout.select", { stack: "panel-body", child: VIEW });
    run("layout.show", { id: "panel" });
  }

  render() {
    return div();
  }
}
