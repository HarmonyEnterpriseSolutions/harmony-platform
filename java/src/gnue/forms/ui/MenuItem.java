package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class MenuItem extends Widget implements ActionListener {

	/** == component */
	private JMenuItem menuItem;

	public MenuItem(Desktop desktop, Integer id,
			String label,
			String iconFile,
			Boolean check
	) {
		super(desktop, id);

		if (check)
			menuItem = new JCheckBoxMenuItem();
		else
			menuItem = new JMenuItem();

		setComponent(menuItem);

		//ystem.out.println(iconFile);

		if (iconFile.length() > 0) {
			menuItem.setIcon(getDesktop().getStaticResourceIcon(iconFile));
		}

		menuItem.setText(label);
		menuItem.addActionListener(this);
	}

	public void uiCheck(Boolean check) {
		((JCheckBoxMenuItem)menuItem).setState(check);
	}

	public void actionPerformed(ActionEvent event) {
		callAfter("onMenu");
	}

}
