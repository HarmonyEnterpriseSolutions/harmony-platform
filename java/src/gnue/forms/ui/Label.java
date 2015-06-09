package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;

public class Label extends Widget {

	public Label(Desktop desktop, Integer id, String text, String alignment) {
		super(desktop, id);
		setComponent(new JLabel(text));
		if (Box.DEBUG) {
			getComponent().setBorder(BorderFactory.createEtchedBorder());
		}
	}

	public void uiSetText(String value) {
		((JLabel)getComponent()).setText(value);
	}
}
