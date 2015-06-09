package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class ToolButton extends Widget {

	AbstractButton button;

	public ToolButton(Desktop desktop, Integer id, String label, String icon, Boolean toggle) {
		super(desktop, id);
		button = toggle ? new JToggleButton() : new JButton();
		button.setMargin(new Insets(0, 0, 0, 0));
		//button.setBorder(null);
		button.setFocusable(false);
		button.setIcon(desktop.getStaticResourceIcon(icon));
		if (label.length() > 0) {
			button.setToolTipText(label);
		}
		button.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				callAfter("onButton");
			}
		});
		setComponent(button);
	}

	public void uiCheck(Boolean check) {
		button.setSelected(check);
	}

}
