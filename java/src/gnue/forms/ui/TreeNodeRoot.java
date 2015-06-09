package gnue.forms.ui;

import javax.swing.tree.*;
import org.json.*;
import java.util.*;

class TreeNodeRoot extends TreeNodeAbstract {

	private String rootId;

	public TreeNodeRoot(Tree tree, String rootId) {
		super(tree);
		this.rootId = rootId;
		childrenValid = true; // root is valid and without children at start
	}

	public String getId() {
		return rootId;
	}

	public int getChildCount() {
		return getChildren().size();
	}

	public TreeNode getParent() {
		return null;
	}

	public TreePath getTreePath(JSONArray path) {
		Vector<TreeNodeAbstract> res = new Vector<TreeNodeAbstract>();
		TreeNodeAbstract node = this;
		res.add(this);
		for (int i = 0; i < path.length() && node != null; i++) {
			node = node.getChildById(path.getString(i));
			if (node != null) {
				res.add(node);
			}
			else {
				break;
			}
		}
		return new TreePath(res.toArray());
	}

}
