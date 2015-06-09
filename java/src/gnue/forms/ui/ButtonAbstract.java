package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class ButtonAbstract extends WidgetNavigable implements ActionListener {

	public ButtonAbstract(Desktop desktop, Integer id, String label, String tip) {
		super(desktop, id, label, tip);
	}
	
	protected void setComponent(JComponent component) {
		super.setComponent(component);
		((AbstractButton)component).addActionListener(this);
	}
	
	public AbstractButton getButtonComponent() {
		return (AbstractButton)getComponent();
	}

	public void actionPerformed(ActionEvent event) {
		call("onButton");
	}

	public void uiPopupMenu(Widget menu) {
		((JPopupMenu)menu.getComponent()).show(getComponent(), getComponent().getWidth()-1, 0);
	}
	
	protected boolean isNavigationEvent(KeyEvent event) {
		// pass enter to server, server will onButton
		switch (event.getKeyCode()) {
			case KeyEvent.VK_ENTER:
				return true;
			default:
				return super.isNavigationEvent(event);
		}
	}
	
}
