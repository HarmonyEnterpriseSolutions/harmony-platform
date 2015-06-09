package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class EntryButton extends Widget implements ActionListener {

	public EntryButton(Desktop desktop, Integer id, String label) {
		super(desktop, id);
		JButton button = new JButton(label);
		setComponent(button);
		button.addActionListener(this);
	}
	
	protected void setComponent(JComponent component) {
		super.setComponent(component);
	}
	
	public void actionPerformed(ActionEvent event) {
		callAfter("onButton");
	}

}
