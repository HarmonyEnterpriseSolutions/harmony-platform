package gnue.forms.ui;

import javax.swing.*;
import javax.swing.tree.*;
import org.json.*;


class TreeNodeRegular extends TreeNodeAbstract {

	private TreeNode parent;
	private JSONObject data;
	private boolean checked = false;

	/**
	 * Method TreeDoc
	 *
	 *
	 */
	public TreeNodeRegular(Tree tree, TreeNode parent, JSONObject data) {
		super(tree);
		this.parent = parent;
		this.data = data;
		this.checked = getNodeStyle().optBoolean("checked", false);
	}

	public String getId() {
		return data.getString("id");
	}

	public int getChildCount() {
		return data.getInt("childCount");
	}

	public TreeNode getParent() {
		return parent;
	}

	public String toString() {
		return data.getString("name");
	}
	
	public void setNodeName(String name) {
		data.put("name", name);
	}
	
	public void setNodeStyle(String style) {
		data.put("nodeStyle", style);
	}

	public JSONObject getNodeStyle() {
		return getTree().getNodeStyle(data.getString("nodeStyle"));
	}

	public boolean isCheckable() {
		return getNodeStyle().optString("button", "").equals("checkbox");
	}

	public boolean isChecked() {
		return checked;
	}

	public void setChecked(boolean checked) {
		this.checked = checked;
	}
}
