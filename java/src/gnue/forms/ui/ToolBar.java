package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class ToolBar extends Widget {

	private JToolBar toolBar;

	public ToolBar(Desktop desktop, Integer id) {
		super(desktop, id);
		toolBar = new JToolBar();
		toolBar.setFloatable(false);
		setComponent(toolBar);
	}

	public void uiAddToolButton(Widget toolButton) {
		toolBar.add(toolButton.getComponent());
	}

	public void uiAddSeparator() {
		toolBar.addSeparator();
	}
}
