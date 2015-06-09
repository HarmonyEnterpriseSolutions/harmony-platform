package gnue.forms.ui;

import javax.swing.*;
import javax.swing.tree.*;
import org.json.*;
import java.util.*;

abstract class TreeNodeAbstract implements TreeNode {

	private Vector<TreeNodeRegular> children = new Vector<TreeNodeRegular>();
	protected boolean childrenValid = false; // valid and has 0 children at start
	private Tree tree;

	/**
	 * Method TreeDoc
	 *
	 *
	 */
	public TreeNodeAbstract(Tree tree) {
		this.tree = tree;
	}

	public abstract String getId();

	public Enumeration children(){
		return getChildren().elements();
	}

	public boolean getAllowsChildren() {
		return getChildren().size() > 0;
	}

	public TreeNode getChildAt(int childIndex){
		return (TreeNode)getChildren().get(childIndex);
	}

	public abstract int getChildCount();

	public int getIndex(TreeNode node) {
		return getChildren().indexOf(node);
	}

	public boolean isLeaf() {
		return getChildCount() == 0;
	}

	public Vector<TreeNodeRegular> getChildren() {
		if (!childrenValid) {
			children.clear();
			JSONArray res = (JSONArray)tree.call("onGetChildren", getId());
			children.ensureCapacity(res.length());
			for (int i=0; i<res.length(); i++) {
				children.add(new TreeNodeRegular(tree, this, (JSONObject)res.get(i)));
			}
			childrenValid = true;

			// update checked pathes in renderer
			TreeCheckableCellRenderer renderer = (TreeCheckableCellRenderer)((JTree)tree.getFocusComponent()).getCellRenderer();

			if (!renderer.isChecked(getTreePath())) {
				for (TreeNodeRegular node: children) {
					renderer.setChecked(node.getTreePath(), node.isChecked());
				}
				if (children.size() > 0) {
					renderer.postCheckedNodes();
				}
			}
		}
		return children;
	}

	public void invalidateChildren() {
		childrenValid = false;
		children.clear(); // to save memory
	}

	public TreePath getTreePath() {
		Vector<Object> path = new Vector<Object>();
		TreeNode node = this;
		while (node != null) {
			path.insertElementAt(node, 0);
			node = node.getParent();
		}
		return new TreePath(path.toArray());
	}

	public TreeNodeAbstract getChildById(String id) {
		for (TreeNodeAbstract treeNode: getChildren()) {
			if (treeNode.getId().equals(id)) {
				return treeNode;
			}
		}
		return null;
		//throw new RuntimeException("Tree node with id '"+getId()+"' has no child with id '"+getId()+"'");
	}

	Tree getTree() {
		return tree;
	}

}


