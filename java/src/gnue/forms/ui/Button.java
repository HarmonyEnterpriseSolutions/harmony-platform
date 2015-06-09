package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

public class Button extends ButtonAbstract {

	public Button(Desktop desktop, Integer id, String label, String tip) {
		super(desktop, id, null, tip);
		setComponent(new JButton(label));
	}

}
