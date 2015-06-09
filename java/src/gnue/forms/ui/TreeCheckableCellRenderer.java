package gnue.forms.ui;
import javax.swing.*;
import javax.swing.tree.*;
import java.awt.*;
import org.json.*;

/**
 * @(#)TreeCheckableCellRenderer.java
 *
 *
 * @author
 * @version 1.00 2009/6/10
 */


public class TreeCheckableCellRenderer extends CheckBoxTreeCellRenderer {

	public TreeCheckableCellRenderer(JTree tree) {
		super(tree, new TreeStyledCellRenderer());
	}

	public Component getTreeCellRendererComponent(
		JTree jtree,
		Object value,
		boolean sel,
		boolean expanded,
		boolean leaf,
		int row,
		boolean hasFocus
	) {
		try {
			TreeNodeRegular treeNode = (TreeNodeRegular) value;
			if (treeNode.isCheckable()) {
				return super.getTreeCellRendererComponent(jtree, value, sel, expanded, leaf, row, hasFocus);
			}
		}
		catch (ClassCastException e) {
			// pass for TreeNodeRoot
		}
		return renderer.getTreeCellRendererComponent(jtree, value, sel, expanded, leaf, row, hasFocus);

	}

	public void toggleChecked(int row) {
		super.toggleChecked(row);
		postCheckedNodes();
	}

	public void postCheckedNodes() {
		// inform server about checked nodes
		JSONArray ids = new JSONArray();
		for (TreePath path: getCheckedPaths()) {
			TreeNodeAbstract node = (TreeNodeAbstract) path.getLastPathComponent();
			ids.put(node.getId());
		}
		((TreeNodeRoot)tree.getModel().getRoot()).getTree().callAfter("onNodesChecked", ids);
	}

}
