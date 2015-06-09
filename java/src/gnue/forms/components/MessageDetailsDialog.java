package gnue.forms.components;

import javax.swing.JDialog;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.border.*;

public class MessageDetailsDialog extends JDialog {
	
	private JTextArea taMessage;
	private JScrollPane spDetails;
	private JTextArea taDetails;
	private JButton buttonClose;
	private JButton buttonDetails;
	private boolean detailsVisible;

	public MessageDetailsDialog(final Component parent, String title, String message, String details, int messageType, boolean isDetailsVisible) {
        super(Utils.getTopLevelFrame(parent), title, true);

		this.detailsVisible = isDetailsVisible;
		
		taMessage = new JTextArea(message);
		taMessage.setBackground(null);
		taMessage.setEditable(false);
		taMessage.setBorder(null);
		//taMessage.setLineWrap(true);
		//taMessage.setWrapStyleWord(true);
		
		taDetails = new JTextArea(details);
		taDetails.setEditable(false);
		
		spDetails = new JScrollPane(taDetails);
		
		buttonClose = new JButton("Close");
		buttonClose.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				close();
			}
		});
		
		buttonDetails = new JButton(getDetailsLabel(detailsVisible));
		buttonDetails.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				detailsVisible = !detailsVisible;
				spDetails.setVisible(detailsVisible);
				buttonDetails.setText(getDetailsLabel(detailsVisible));
				pack();
		        setLocationRelativeTo(parent);
			}
		});

        JPanel north = new JPanel(new GridBagLayout());

		GridBagConstraints cs = new GridBagConstraints();

		//cs.anchor = cs.NORTHWEST;
		cs.insets = new Insets(5,5,5,0);
		north.add(new JLabel(getBuiltinImage(messageType)), cs);

		cs.gridx = 1;
		cs.weightx = 1;
		cs.fill = cs.BOTH;
		north.add(taMessage, cs);

		cs.gridwidth = 2;
		cs.gridx = 0;
		cs.gridy = 1;
		cs.weighty = 1;
        north.add(spDetails, cs);

        JPanel south = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        
        south.add(buttonClose);
        south.add(buttonDetails);
        
        add(north, BorderLayout.CENTER);
        add(south, BorderLayout.SOUTH);
        
        // must pack with details visible because message have small width
        //pack();

		spDetails.setVisible(detailsVisible);
		pack();

        setLocationRelativeTo(parent);
        setModal(true);
        setVisible(true);
    }
    
    public void pack() {
		spDetails.setPreferredSize(new Dimension(800, Math.min(taDetails.getPreferredSize().height+20, 400))); // 20 is horizontal scrollbar height
    	super.pack();
    }
    
    protected String getDetailsLabel(boolean detailsVisible) {
    	return detailsVisible ? "Details <<" : "Details >>";
    }

	public void close() {
		setVisible(false);
		dispose();
	}
    
	protected JRootPane createRootPane() {
		JRootPane rootPane = new JRootPane();
		KeyStroke stroke = KeyStroke.getKeyStroke("ESCAPE");
		Action actionListener = new AbstractAction() {
			public void actionPerformed(ActionEvent actionEvent) {
				close();
			}
		};
		InputMap inputMap = rootPane.getInputMap(JComponent.WHEN_IN_FOCUSED_WINDOW);
		inputMap.put(stroke, "ESCAPE");
		rootPane.getActionMap().put("ESCAPE", actionListener);
		return rootPane;
	}

	public static ImageIcon getBuiltinImage(String name) {
		java.net.URL url = UIManager.getLookAndFeel().getClass().getResource("icons/" + name + ".gif");
		if (url == null) {
			url = UIManager.getLookAndFeel().getClass().getResource("icons/" + name + ".png");
		}
		return (url != null) ? new ImageIcon(url) : new ImageIcon();
	}

	public static ImageIcon getBuiltinImage(int messageType) {
		switch(messageType) {
			case JOptionPane.ERROR_MESSAGE:       return getBuiltinImage("Error");
			case JOptionPane.INFORMATION_MESSAGE: return getBuiltinImage("Inform");
			case JOptionPane.WARNING_MESSAGE:     return getBuiltinImage("Warn");
			case JOptionPane.QUESTION_MESSAGE:    return getBuiltinImage("Question");
			default: return new ImageIcon();
		}
	}

	public static void main(String[] args) {
        MessageDetailsDialog dlg = new MessageDetailsDialog(null, "Title!", "Error message", "Error details", JOptionPane.ERROR_MESSAGE, false);
        dlg.setVisible(true);
	}
}
