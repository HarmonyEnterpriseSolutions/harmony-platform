package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class Panel extends Widget {

	private JPanel panel;

	public Panel(Desktop desktop, Integer id) {
		super(desktop, id);
		panel = new JPanel();
		setComponent(panel);
		panel.setLayout(new BorderLayout());
	}

	public void uiAdd(Widget widget) {
		panel.add(widget.getComponent(), BorderLayout.CENTER);
	}

}
