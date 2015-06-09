package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class PopupMenu extends Widget /*implements ActionListener*/ {

	/** == component */
	protected JPopupMenu menu;

	public PopupMenu(Desktop desktop, Integer id, String label) {
		super(desktop, id);
		menu = new JPopupMenu(label);
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

}
