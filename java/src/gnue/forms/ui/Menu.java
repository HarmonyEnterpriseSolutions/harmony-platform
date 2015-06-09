package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class Menu extends Widget /*implements ActionListener*/ {

	/** == component */
	protected JMenu menu;

	public Menu(Desktop desktop, Integer id, String label) {
		super(desktop, id);
		menu = new JMenu(label);
		setComponent(menu);
		//menu.addActionListener(this);
	}

	public void uiAddSeparator() {
		menu.addSeparator();
	}

	public void uiAddMenu(Widget menuItem) {
		menu.add((JMenuItem)menuItem.getComponent());
	}

	public void uiRemoveAll() {
		menu.removeAll();
	}
	
	public void uiEnable(Boolean enabled) {
		menu.enable(enabled);
	}

}
