package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import gnue.forms.rpc.RpcException;
import org.json.*;

public class Splitter extends Widget {

	private JSplitPane splitPane;

	public Splitter(Desktop desktop, Integer id, Boolean vertical) {
		super(desktop, id);
		splitPane = new JSplitPane( !vertical ? JSplitPane.VERTICAL_SPLIT : JSplitPane.HORIZONTAL_SPLIT);
		splitPane.setResizeWeight(0.5);
		setComponent(splitPane);
	}

	public void uiAdd(Widget widget) {
		if (splitPane.getLeftComponent() == null) {
			splitPane.setLeftComponent(widget.getComponent());
		}
		else {
			if (splitPane.getRightComponent() == null) {
				splitPane.setRightComponent(widget.getComponent());
			}
			else {
				throw new RuntimeException("Splitter allows only two panes");
			}
		}
	}

	public boolean isVerticalGrowable() {
		return true;
	}

	//////////////////////////////////////////////////////////////////////////////
	// state
	//
	public JSONObject getState() {
		JSONObject state = new JSONObject();
		state.put("dividerLocation", splitPane.getDividerLocation());
		return state;
	}

	public void setState(JSONObject state) {
		splitPane.setDividerLocation(state.getInt("dividerLocation"));
	}
}
