package gnue.forms.ui;

import javax.swing.*;
import javax.swing.tree.*;
import java.awt.*;
import org.json.*;
import java.util.*;

class TreeStyledCellRenderer extends DefaultTreeCellRenderer {

	private static Map<Integer, Color> colors = new HashMap<Integer, Color>();

	public TreeStyledCellRenderer() {
	}

	protected static Color getColor(int srgb) {
		Color color = colors.get(srgb);
		if (color == null) {
			colors.put(srgb, color = new Color(srgb));
		}
		return color;
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
		JLabel cell = (JLabel) super.getTreeCellRendererComponent(jtree, value, sel, expanded, leaf, row, hasFocus);

		try {
			TreeNodeRegular treeNode = (TreeNodeRegular) value;
			JSONObject nodeStyle = treeNode.getNodeStyle();
			Tree tree = treeNode.getTree();

			if (nodeStyle.has("icon")) {
				cell.setIcon(tree.getDesktop().getStaticResourceIcon(nodeStyle.getString("icon")));
			}

			cell.setFont(tree.getNodeFont(nodeStyle, cell.getFont()));

			if (nodeStyle.has("textcolor")) {
				cell.setForeground(getColor(nodeStyle.getInt("textcolor")));
			}
			if (nodeStyle.has("bgcolor")) {
				cell.setBackground(getColor(nodeStyle.getInt("bgcolor")));
			}

		}
		catch (ClassCastException e) {
			// pass for TreeNodeRoot
		}
		return cell;
	}

}
