package gnue.forms.ui;

import javax.swing.*;
import java.awt.*;

public class HBox extends Box {

	private static GridBagConstraints CS;
	private static GridBagConstraints CS_LABEL;
	private static Insets FIRST_INSETS = new Insets(0,0,0,0);
	private static Insets REGULAR_INSETS = new Insets(0,INSETX,0,0);

	static {
		// constraints init
		CS = new GridBagConstraints();

		CS_LABEL = new GridBagConstraints();
		CS_LABEL.fill = GridBagConstraints.BOTH;

	}

	public HBox(Desktop desktop, Integer id, String label, Boolean titled) {
		super(desktop, id, label, titled);
		if (DEBUG) getComponent().setBackground(new Color(100, 255, 100));
	}

	public void uiAddWidgets() {
				
		int x = 0;
		int y = isWidgetLabelPresent() ? 1 : 0;
		boolean needSpacer = true;

		JComponent panel = getComponent();

		for (Widget widget: widgets) {
			
			Insets insets = panel.getComponentCount() == 0 ? FIRST_INSETS : REGULAR_INSETS;
	
			// add label
			JComponent label = widget.getLabel();
			if (label != null) {
				GridBagConstraints cs = (GridBagConstraints)CS_LABEL.clone();
				cs.gridx = x;
				cs.insets = insets;
				panel.add(label, cs);
			}
	
			// calculate normal constraints
			GridBagConstraints cs = (GridBagConstraints)CS.clone();
			cs.gridy   = y;
			cs.gridx   = x;
			cs.weightx = widget.isHorizontalGrowable() ? 1.0 : 0.0;
			cs.weighty = widget.isVerticalGrowable()   ? 1.0 : 0.0;
			cs.insets  = insets;
			cs.fill    = widget.getFill();
			cs.anchor  = widget.getAnchor();
			
			panel.add(widget.getComponent(), cs);
	
			// move right
			x++;
			needSpacer &= !widget.isHorizontalGrowable();
		}

		if (needSpacer) {
			addSpacer();
		}
		
	}
}
