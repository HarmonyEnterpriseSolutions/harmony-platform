package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class MenuBar extends Widget {

	/** == component */
	private JMenuBar menuBar;

	public MenuBar(Desktop desktop, Integer id) {
		super(desktop, id);
		menuBar = new JMenuBar();
		setComponent(menuBar);
	}

	public void uiAddMenu(Widget menu) {
		menuBar.add((JMenu) menu.getComponent());
	}

}
