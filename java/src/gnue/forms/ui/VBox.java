package gnue.forms.ui;

import java.awt.*;
import javax.swing.*;

public class VBox extends Box {

	private static GridBagConstraints CS;
	private static Insets FIRST_INSETS		   = new Insets(INSETY,INSETX,INSETY,INSETX);
	private static Insets FIRST_LABEL_INSETS   = new Insets(INSETY,INSETX,INSETY,0);
	private static Insets REGULAR_INSETS	   = new Insets(0,	   INSETX,INSETY,INSETX);
	private static Insets REGULAR_LABEL_INSETS = new Insets(0,	   INSETX,INSETY,0);

	static {
		// constraints init
		CS = new GridBagConstraints();
		CS.fill = GridBagConstraints.BOTH;
	}

	public VBox(Desktop desktop, Integer id, String label, Boolean titled) {
		super(desktop, id, label, titled);
		if (DEBUG) getComponent().setBackground(new Color(255, 100, 100));
	}

	public void uiAddWidgets() {
		
		JComponent panel = getComponent();

		for (Widget widget: widgets) {
			boolean first = panel.getComponentCount() == 0;
	
			GridBagConstraints cs = (GridBagConstraints)CS.clone();
	
			// add label
			JLabel label = widget.getLabel();
			if (label != null) {
				cs.insets = first ? FIRST_LABEL_INSETS : REGULAR_LABEL_INSETS;
				if (widget.isVerticalGrowable()) {
					label.setVerticalAlignment(JLabel.TOP);
				}
				panel.add(label, cs);
			}
	
			cs.insets    = first ? FIRST_INSETS : REGULAR_INSETS;
			cs.weightx   = 1.0;
			cs.weighty   = widget.isVerticalGrowable() ? 1.0 : 0.0;
			cs.gridwidth = GridBagConstraints.REMAINDER;
			cs.fill      = widget.getFill();
			cs.anchor    = widget.getAnchor();
	
			panel.add(widget.getComponent(), cs);
		}
		if (!isVerticalGrowable()) {
			addSpacer();
		}
	}
}
