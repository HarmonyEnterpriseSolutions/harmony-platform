package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import javax.swing.tree.*;
import org.json.*;
import java.util.*;
import java.awt.Font;
import java.awt.event.*;

public class Tree extends WidgetNavigable implements TreeSelectionListener, MouseListener {

	private JTree tree;
	JPopupMenu popupMenu = null;

	// cache prefilled in init
	private Map<String, JSONObject> nodeStyles = new HashMap<String, JSONObject>();
	private Map<JSONObject, Font> nodeFonts = new HashMap<JSONObject, Font>();

	public Tree(Desktop desktop, Integer id, String label, final String rootId, JSONArray nodeStyles) {
		super(desktop, id, label);

		// frefill cache
		for (int i=0; i<nodeStyles.length(); i++) {
			JSONObject nodeStyle = nodeStyles.getJSONObject(i);
			this.nodeStyles.put(nodeStyle.getString("name"), nodeStyle);
		}

		tree = new JTree(new DefaultTreeModel(new TreeNodeRoot(Tree.this, rootId)));
		tree.setShowsRootHandles(true);
		tree.setRootVisible(false);
		tree.addTreeSelectionListener(this);
		tree.setCellRenderer(new TreeCheckableCellRenderer(tree));

		setComponent(new JScrollPane(tree));

		tree.addMouseListener(this);
	}

	public JComponent getFocusComponent() {
		return tree;
	}

	public TreeNodeRoot getRoot() {
		return (TreeNodeRoot)tree.getModel().getRoot();
	}

	public JSONObject getNodeStyle(String key) {
		JSONObject nodeStyle = nodeStyles.get(key);
		if (nodeStyle == null) {
			nodeStyle = (JSONObject)call("onGetNodeStyle", key);
			nodeStyles.put(key, nodeStyle);
		}
		return nodeStyle;
	}

	public Font getNodeFont(JSONObject nodeStyle, Font proto) {
		Font font = nodeFonts.get(nodeStyle);
		if (font == null) {

			boolean bold   = nodeStyle.optBoolean("bold", false);
			boolean italic = nodeStyle.optBoolean("italic", false);

			int fontStyle = proto.getStyle();
			fontStyle = bold   ? (fontStyle | Font.BOLD)   : (fontStyle & ~Font.BOLD);
			fontStyle = italic ? (fontStyle | Font.ITALIC) : (fontStyle & ~Font.ITALIC);

			if (fontStyle != proto.getStyle()) {
				font = proto.deriveFont(fontStyle);
			}
			else {
				font = proto;
			}
		}
		return font;
	}

	public void uiRevalidate() {
		tree.removeTreeSelectionListener(this);
		try {
			getRoot().invalidateChildren();
			((DefaultTreeModel)tree.getModel()).nodeStructureChanged(getRoot());

			// expand first layer
			for (TreeNodeAbstract child: getRoot().getChildren()) {
				tree.expandPath(child.getTreePath());
			}
		}
		finally {
			tree.addTreeSelectionListener(this);
		}
	}

	public void uiRevalidateIdPath(JSONArray path, Boolean nameChanged, Boolean styleChanged, String nodeName, String nodeStyle) {
		TreeNode node = (TreeNode)getRoot().getTreePath(path).getLastPathComponent();
		if (node instanceof TreeNodeRegular) {
			if (nameChanged) {
				((TreeNodeRegular)node).setNodeName(nodeName);
			}
			if (styleChanged) {
				((TreeNodeRegular)node).setNodeStyle(nodeStyle);
			}
			((DefaultTreeModel)tree.getModel()).nodeChanged(node);
		}
	}

	public void uiSelectIdPath(JSONArray path) {
		tree.removeTreeSelectionListener(this);
		try {
			tree.setSelectionPath(getRoot().getTreePath(path));
		}
		finally {
			tree.addTreeSelectionListener(this);
		}
	}



	public void uiCheckAllNodes(Boolean check) {
		CheckBoxTreeCellRenderer renderer = (CheckBoxTreeCellRenderer)tree.getCellRenderer();
		TreeNodeRoot root = (TreeNodeRoot)tree.getModel().getRoot();
		renderer.setChecked(root.getTreePath(), check);
	}

	public void uiSetPopupMenu(Widget widget) {
		popupMenu = (JPopupMenu)widget.getComponent();
	}

	/**
	 * expand or collapse  all children recursively
	 * if isPath is empty, expands or collapses all
	 */
	public void uiExpandChildren(JSONArray idPath, Boolean expand) {
		TreePath treePath = idPath.length() > 0 ? getRoot().getTreePath(idPath) : null;
		for (int i = 0; i < tree.getRowCount(); i++) {
			TreePath path = tree.getPathForRow(i);
			if (treePath == null || treePath.isDescendant(path)) {
				if (expand) {
					tree.expandPath(path);
				}
				else {
					tree.collapsePath(path);
				}
			}
		}
	}

	public void valueChanged(TreeSelectionEvent event) {
		callAfter("onSelectionChanged", ((TreeNodeAbstract)event.getPath().getLastPathComponent()).getId());
	}

	public boolean isVerticalGrowable() {
		return true;
	}


	// mouse listener
	public void mouseClicked(MouseEvent event) {
		if (event.getClickCount() == 2 && event.getButton() == MouseEvent.BUTTON1) {
			//TreePath selPath = tree.getPathForLocation(event.getX(), event.getY());
			if(tree.getRowForLocation(event.getX(), event.getY()) != -1 ) {
				call("onNodeActivated");
			}
		}
	}
	public void mouseEntered(MouseEvent event) {}
	public void mouseExited(MouseEvent event) {}
	public void mousePressed(MouseEvent event) {
		int row = tree.getRowForLocation(event.getX(), event.getY());
		if (row != -1) {
			tree.setSelectionRow(row);
		}
		mouseMaybePopup(event);
	}
	public void mouseReleased(MouseEvent event) {
		mouseMaybePopup(event);
	}
	private void mouseMaybePopup(final MouseEvent event) {
		if (event.isPopupTrigger()) {
			if (popupMenu != null) {
				// fixes #263, when tree will receive focus, menu will take a correct state
				tree.requestFocus();
				int row = tree.getRowForLocation(event.getX(), event.getY());
				call("onMenuPopup", row != -1 ? ((TreeNodeAbstract)tree.getPathForRow(row).getLastPathComponent()).getId() : "None");
				popupMenu.show((JComponent)event.getSource(), event.getX(), event.getY());
			}
		}
	}

	/**
	 * invoked by WidgetNavigable.keyListener
	 * registered to component in WidgetNavigable.setComponent
	 * use appendCall instead call (appended calls will be flushed)
	 */
	protected boolean onKeyPressed(KeyEvent event) {
		boolean navigation = super.onKeyPressed(event);
		if (!navigation) {
			if (event.getKeyCode() == KeyEvent.VK_ENTER) {
				appendCall("onNodeActivated");
			}
		}
		return navigation;
	}

}
