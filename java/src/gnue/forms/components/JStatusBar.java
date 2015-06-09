package gnue.forms.components;

import javax.swing.*;
import javax.swing.border.*;
import java.awt.*;


public class JStatusBar extends JPanel {

	JLabel[] labels;
	private static GridBagConstraints cs = new GridBagConstraints();

	public JStatusBar(int[] labelWidths) {
		super(new GridBagLayout());

		cs.fill = GridBagConstraints.BOTH;
		cs.weighty = 0.0;
		//cs.gridwidth = labelWidths.length;
		//cs.gridheight = 1;
		//cs.gridy = 0;

		labels = new JLabel[labelWidths.length];

		for (int i=0; i<labelWidths.length; i++) {
			int width = labelWidths[i];

			JLabel label = new JLabel(" ");
			label.setBorder(BorderFactory.createEtchedBorder());

			Dimension size = label.getPreferredSize();
			if (width >= 0) {
				size.width = width;
				label.setPreferredSize(size);
				cs.weightx = 0.0; // no extra space needed
			}
			else {
				cs.weightx = 1.0;
			}
			//cs.gridx = i;

			labels[i] = label;

			add(label, cs);
		}
	}

	public void setStatusText(String text, Integer pos) {
		labels[pos].setText(text);
	}

}
