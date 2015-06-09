package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;

public class EntryPassword extends EntryAbstractText {

	public EntryPassword(Desktop desktop, Integer id, String label, String tip, Integer align) {
		super(desktop, id, label, tip, align);
		setComponent(new JPasswordField());
	}

}
