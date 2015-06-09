package gnue.forms.ui;

import java.awt.*;
import javax.swing.*;
import java.util.List;
import java.util.ArrayList;

public class Box extends Widget {

	final static boolean DEBUG = false;
	public static int INSETX = 5;
	public static int INSETY = 5;

	private final static GridBagConstraints CS_SPACER = new GridBagConstraints();

	private boolean titled;
	protected List<Widget> widgets = new ArrayList<Widget>();

	static {
		// constraints init
		CS_SPACER.fill = GridBagConstraints.BOTH;
		//CS_SPACER.insets = new Insets(0,0,0,0);
		CS_SPACER.weightx = 1.0;
		CS_SPACER.weighty = 1.0;
		CS_SPACER.gridwidth = GridBagConstraints.REMAINDER;
		CS_SPACER.gridheight = GridBagConstraints.REMAINDER;
	}

	public Box(Desktop desktop, Integer id, String label, boolean titled) {
		super(desktop, id, label);
		this.titled = titled;

		JPanel panel = new JPanel();
		panel.setLayout(new GridBagLayout());

		// If any of our children is a VBox or uses a label, we draw a box
		// around ourselves. Otherwise, use the label column of the containing
		// box.

		if (titled) {
			panel.setBorder(new javax.swing.border.TitledBorder(label));
		}
		setComponent(panel);
	}

	protected void addSpacer() {
		// add spacer if no weight
		Dimension zero = new Dimension(0,0);
		JPanel spacer = new JPanel();
		spacer.setMinimumSize(zero);
		spacer.setPreferredSize(zero);
		if (DEBUG) spacer.setBackground(Color.DARK_GRAY);
		getComponent().add(spacer, CS_SPACER);
	}

	/**
	 * returns null. boxes drawing labels internally
	 */
	public JLabel getLabel() {
		return titled ? null : super.getLabel();
	}

	public void uiAdd(Widget widget) {
		widgets.add(widget);
	}

	/** actual after all widgets added */
	public boolean isVerticalGrowable() {
		for (Widget widget: widgets) {
			if (widget.isVerticalGrowable()) {
				return true;
			}
		}
		return false;
	}
	
	/** 
	 * returns true if at list one widget label present 
	 * actual after all widgets added
	 */
	protected boolean isWidgetLabelPresent() {
		for (Widget widget: widgets) {
			if (widget.getLabel() != null) {
				return true;
			}
		}
		return false;
	}


}
