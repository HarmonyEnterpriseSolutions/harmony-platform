package gnue.forms.components;

/**
 * @(#)TextFieldWithButtons.java
 *
 *
 * @author
 * @version 1.00 2009/7/2
 */

import java.util.*;
import javax.swing.*;
import javax.swing.text.JTextComponent;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
//import javax.swing.plaf.basic.BasicArrowButton;

public class TextFieldWithButtons extends JPanel {

	class TextField extends JTextField {
		public TextField() {
			super();
		}
		public boolean processKeyBinding(KeyStroke ks, KeyEvent e, int condition, boolean pressed) {
			return super.processKeyBinding(ks, e, condition, pressed);
		}
	}

	private int buttonCount = 0;
	private TextField textField;

	public TextFieldWithButtons() {
		setLayout(new GridBagLayout());
		setBackground(Color.RED);

		textField = new TextField();

		GridBagConstraints tfcs = new GridBagConstraints();
		tfcs.fill = GridBagConstraints.BOTH;
		tfcs.weightx = 1.0;
		tfcs.weighty = 1.0;

		add(textField, tfcs);
		
		addFocusListener(new FocusAdapter(){
			public void focusGained(FocusEvent event) {
				textField.requestFocus();
			}
		});
		
	}
	
	public void setButtonsEnabled(boolean enabled) {
		for (Component c: this.getComponents()) {
			if (c instanceof AbstractButton) {
				c.setEnabled(enabled);
			}
		}
	}
	
	protected boolean processKeyBinding(KeyStroke ks, KeyEvent e, int condition, boolean pressed) {
		return textField.processKeyBinding(ks, e, condition, pressed);
	}

	public JButton addButton(String text) {
		//BasicArrowButton has problems with preferred size
		//button = new BasicArrowButton(BasicArrowButton.SOUTH);
		JButton button = new JButton(text);
		addButton(button);
		return button;
	}

	public void addButton(AbstractButton button) {
	
		button.setMargin(new Insets(0, 0, 0, 0));

		GridBagConstraints bcs = new GridBagConstraints();
		bcs.fill = GridBagConstraints.BOTH;
		bcs.weightx = 0.0;
		bcs.weighty = 1.0;

		add(button, bcs);
		
		buttonCount += 1;
		
		Dimension tfMinSize = textField.getMinimumSize();
		tfMinSize.width += tfMinSize.height * buttonCount;
		setMinimumSize(tfMinSize);

		Dimension tfPrefSize = textField.getPreferredSize();
		tfPrefSize.width += tfPrefSize.height * buttonCount;
		setPreferredSize(tfPrefSize);

		Dimension buttonSize = new Dimension(tfPrefSize.height, Integer.MAX_VALUE);
		button.setMinimumSize(buttonSize);
		button.setPreferredSize(buttonSize);
		button.setMaximumSize(buttonSize);
	}

	public JTextComponent getTextComponent() {
		return textField;
	}

	///////////////////////////////////////////////////////////////////////////
	// TEST

	public static void main(String args[]) {

		final JFrame frame = new JFrame("TextFieldWithButtons");
		TextFieldWithButtons pc = new TextFieldWithButtons();
		
		pc.addButton(">");
		frame.add(pc);
		//frame.add(new JTextField());
		frame.pack();
		frame.setVisible(true);

		frame.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent evt) {
				frame.dispose();
				System.exit(0);
			}
		});

	}


}
